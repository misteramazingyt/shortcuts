/*
 * macOS port of 0xilis/appleid-key-dumper.
 *
 * The ONLY changes from the upstream iOS main.m are the output paths: upstream
 * hardcodes /var/mobile/Documents/appleid-key-dumper, and this reads a target
 * directory from argv[1] (falling back to $HOME/appleid-dump). The signing and
 * archiving logic is left byte-for-byte identical, because shortcut-sign
 * consumes exactly this output format — "improving" it would break that.
 *
 * What it does, and why it can work on macOS where key *export* cannot:
 * it never exports your Apple ID private key. It generates a fresh, extractable
 * ECDSA-P256 keypair, uses the Apple ID key to sign that new key's public half
 * once, and writes out the new key plus an auth blob proving Apple endorses it.
 * Using the key is allowed even when copying it out is not.
 *
 * Reaching the Apple ID key needs the keychain-access-group entitlement in
 * entitlements.plist, which a normally-signed binary cannot claim — hence the
 * AMFI/SIP steps in README.md.
 */

#import <Foundation/Foundation.h>
#import <Security/Security.h>
#import "Sharing/SFAppleIDAccount.h"

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/stat.h>
#include <string.h>

int main(int argc, char **argv) {
    @autoreleasepool {
        /* Where to write. argv[1], else $HOME/appleid-dump. */
        const char *outDir = (argc > 1) ? argv[1] : NULL;
        NSString *dir;
        if (outDir) {
            dir = [NSString stringWithUTF8String:outDir];
        } else {
            const char *home = getenv("HOME");
            if (!home) {
                fprintf(stderr, "appleid-key-dumper: no output dir and $HOME unset\n");
                return -1;
            }
            dir = [NSString stringWithFormat:@"%s/appleid-dump", home];
        }

        NSData *plist = (__bridge NSData *) CFPreferencesCopyValue((CFStringRef)@"AppleIDAccount",
            (CFStringRef)@"com.apple.sharingd",
            (CFStringRef)kCFPreferencesCurrentUser,
            (CFStringRef)kCFPreferencesCurrentHost);

        if (!plist) {
            fprintf(stderr,
                "appleid-key-dumper: could not read AppleIDAccount from com.apple.sharingd.\n"
                "  Is this Mac signed into iCloud? System Settings > Apple Account.\n");
            return -1;
        }

        SFAppleIDAccount *account = [NSKeyedUnarchiver unarchivedObjectOfClass:SFAppleIDAccount.class fromData:plist error:NULL];
        if (!account) {
            fprintf(stderr, "appleid-key-dumper: failed to decode SFAppleIDAccount\n");
            return -1;
        }

        /* Confirmation for the operator — which account is being dumped. */
        fprintf(stderr, "appleid-key-dumper: account = %s\n", [[account appleID] UTF8String] ?: "(unknown)");

        /* Get the SFAppleIDIdentity from it */
        SFAppleIDIdentity *identity = [account identity];

        /* Get the certificates from that identity */
        SecCertificateRef cert = (SecCertificateRef)[[account identity] copyCertificate];
        SecCertificateRef intercert = (SecCertificateRef)[[account identity] copyIntermediateCertificate];

        /* Get private key from Apple ID. This will be used to sign a public key that we will randomly generate. */
        SecKeyRef privateKey = (SecKeyRef)[identity copyPrivateKey];
        if (!privateKey) {
            fprintf(stderr,
                "appleid-key-dumper: copyPrivateKey returned NULL.\n"
                "  The entitlement did not grant keychain access. This is the step\n"
                "  that fails on a VM or with AMFI still enabled.\n");
            return -1;
        }

        /* Generate an ECDSA-P256 key */
        NSMutableDictionary *mutableDict = [NSMutableDictionary dictionary];
        mutableDict[(__bridge id)kSecAttrKeyType] = (__bridge id)kSecAttrKeyTypeECSECPrimeRandom;
        mutableDict[(__bridge id)kSecAttrKeySizeInBits] = @256;
        mutableDict[(__bridge id)kSecAttrIsPermanent] = @NO;

        SecKeyRef key = SecKeyCreateRandomKey((__bridge CFDictionaryRef)mutableDict, 0);

        /* Get public key */
        SecKeyRef pubKey = SecKeyCopyPublicKey(key);
        NSData *signingPublicKey = (__bridge NSData *)SecKeyCopyExternalRepresentation(pubKey, 0);

        /* Sign it with the Apple ID private key */
        CFErrorRef error = NULL;
        CFDataRef data = SecKeyCopyExternalRepresentation(pubKey, &error);
        NSData *signature = (__bridge NSData *)SecKeyCreateSignature(privateKey, kSecKeyAlgorithmRSASignatureMessagePSSSHA256, data, &error);

        /* Generate auth data */
        NSMutableDictionary *dict = [NSMutableDictionary dictionaryWithDictionary:@{
            @"AppleIDCertificateChain" : @[
                (__bridge NSData *)SecCertificateCopyData(cert),
                (__bridge NSData *)SecCertificateCopyData(intercert),
            ],
            @"SigningPublicKey" : signingPublicKey,
            @"SigningPublicKeySignature" : signature,
            @"AppleIDValidationRecord" : [account validationRecord],
        }];

        NSData *authData = [NSKeyedArchiver archivedDataWithRootObject:dict];

        /* Ensure the output directory exists. */
        mkdir([dir UTF8String], 0755);

        NSString *authPath = [dir stringByAppendingPathComponent:@"authData.plist"];
        NSString *keyPath  = [dir stringByAppendingPathComponent:@"privateKey.bin"];

        printf("writing to %s ...\n", [dir UTF8String]);
        [authData writeToFile:authPath atomically:FALSE];

        CFErrorRef errorer = NULL; /* its called errorer because its more error */
        CFDataRef keyData = SecKeyCopyExternalRepresentation(key, &errorer);
        if (errorer) {
            fprintf(stderr,"appleid-key-dumper: failed to copy key representation\n");
            return -1;
        }
        NSData *data2 = (__bridge NSData *)keyData;
        [data2 writeToFile:keyPath atomically:FALSE];

        printf("wrote private key and auth data to %s\n", [dir UTF8String]);
        return 0;
    }
}
