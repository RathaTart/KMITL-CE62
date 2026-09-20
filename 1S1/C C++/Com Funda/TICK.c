#include <stdio.h>

int main(void)
{
    int X, rem;
    printf("Enter X: ");
    scanf("%d", &X);
    rem = X % 2;
    if (rem == 0)
        printf("%d (Even)\n", X);
    else if(rem == 2)
        printf("%d (odd)\n", X);
    else if(rem == 1)
        printf("Love Tart");
}

