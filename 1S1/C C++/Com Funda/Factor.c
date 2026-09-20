
#include<stdio.h>

int main()
{
    int input;
    printf("Enter number : ");
    scanf("%d", &input);

    int number = input;
    printf("Factoring Result : ");
    if(number == 1)
    {
        printf("1");
    }
    for(int i=2; i<=input; i)
    {
        if((number%i == 0)&&(number != i))
        {
            printf("%d x ", i);
            number = number/i;
        }
        else if((number%i == 0)&&(number == i))
        {
            printf("%d", i);
            break;
        }
        else
        {
            i++;
        }
    }


    return 0;
}

