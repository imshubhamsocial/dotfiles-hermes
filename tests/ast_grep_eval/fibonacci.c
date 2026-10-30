#include <stdio.h>

long long calculate_fibonacci(int n) {
    if (n <= 0) return 0;
    if (n == 1) return 1;
    long long a = 0, b = 1, c = 0;
    for (int i = 2; i <= n; i++) {
        c = a + b;
        a = b;
        b = c;
    }
    return b;
}

int main(void) {
    int n = 10;
    printf("Fibonacci(%d) = %lld\n", n, calculate_fibonacci(n));
    return 0;
}
