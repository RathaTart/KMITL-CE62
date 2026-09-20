#include<stdio.h>

int multiply(int a)
{
    for(int i=1; i<=12; i++)
    {
        printf("%d * %d = %d\n", a, i, a*i);
    }
    return 0;
}

int main(){

    int number;
    scanf("%d", &number);
    multiply(number);

    return 0;
}
