#include <unistd.h>

int retone() { return 1; }

#define getreg(dest, src)                                                              \
    register long long dest __asm__(#src);                                             \
    __asm__("" : "=r"(dest));

int main() {
    int a = 0;

    getreg(arg3, r10);
    // read(0, (char*)arg3, (int)(arg3+8));
    a = retone();
    return a;
}