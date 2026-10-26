#include <stdio.h>
#include <string.h>

typedef struct TokenHeader {
    char alg[16];
    char typ[16];
    int version;
} TokenHeader;

typedef struct TenantContext {
    char tenant_id[64];
    unsigned long salt;
} TenantContext;

unsigned long compute_tenant_hash(const char *tenant_id, unsigned long salt) {
    unsigned long hash = 5381 ^ salt;
    int c;
    while ((c = *tenant_id++)) {
        hash = ((hash << 5) + hash) + c;
    }
    return hash;
}

int verify_tenant_token_header(const TokenHeader *hdr) {
    if (strcmp(hdr->alg, "RS256") == 0 || strcmp(hdr->alg, "ES256") == 0) {
        return 1;
    }
    return 0;
}
