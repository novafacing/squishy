// Test source file for check.c
#include <stdio.h>

void _strcpy(char *a, const char *b) {
    while ((*a++ = *b++))
        ;
}

int _strlen(const char *s) {
    int i = 0;
    for (; *s; s++, i++)
        ;
    return i;
}

int _copier(char *a, const char *b) {
    _strcpy(a, b);
    return _strlen(a);
}

int main(void) {
    char a[0x10] = {0};
    int i = _copier(a, "poodle");
    printf("%s\n", a);
    return i;
}
