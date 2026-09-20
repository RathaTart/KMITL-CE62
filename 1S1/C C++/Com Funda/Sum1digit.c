#include<stdio.h>

int main()
{
    int num, sum=0;
    scanf("%d", &num);
    for(int i=0; i<100; i++)
    {
        sum = num%10+sum;
        num = num/10;
    }
    printf("%d", sum);
}
