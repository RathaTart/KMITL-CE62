
#include<stdio.h>

int main()
{
    int number;
    printf("Enter number : ");
    scanf("%d", &number);
    for(int i=1; i<=number; i++)
    {
        if((i==1)||(i==number))
        {
            for(int j=1; j<=number; j++)
            {
                printf("*");
            }
            printf("\n");
        }
        else
        {
            printf("*");
            for(int j=1; j<=number-2; j++)
            {
                printf(" ");
            }
            printf("*\n");
        }
    }
    return 0;
}
