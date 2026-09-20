#include<stdio.h>

int main()
{
    int num;
    scanf("%d", &num);
    for(int row=0; row<num; row++)
    {
        if(row == 0 || row == num)
        {
            for(int i=0; i<num; i++)
            {
                printf("*");
            }
        }
        else if(row != 0 && row != num)
        {
            for(int i=0; i<num; i++)
            {
                printf("*");
                for(int j=0; j<num-2; j++)
                {
                    printf(" ");
                }
                printf("*");
            }
        }
        printf("\n");
    }



    return 0;
}
