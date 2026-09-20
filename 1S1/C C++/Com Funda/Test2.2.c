#include <stdio.h>

int main()
{
    int num;
    scanf("%d", &num);
    int count = 0;
    int first = 0;
    for(int y = 0; y < num; y++)
    {
        for(int x = 0; x < num; x++)
        {
            if(count%2 == 0)
            {
                printf("*");
            }
            else
            {
                if(first%2 == 0)
                {
                    printf("*");
                }
                else
                {
                    printf(" ");
                }
                first++;
            }

        }
        count++;
        first = 0;
        printf("\n");
    }
    return 0;
}
