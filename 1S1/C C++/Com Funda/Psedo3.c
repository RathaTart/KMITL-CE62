#include<stdio.h>

int main()
{
    int n;
    scanf("%d", &n);
    for(int i=1; i<=n; i++)
    {
        for(int j=1; j<=n; j++)
        {
            if(i%2 == 1)
            {
                if(j%2 == 1)
                {
                    printf("*");
                }
                if(j%2 == 0)
                {
                    printf("_");
                }
            }
            if(i%2 == 0)
            {
                if(j%2 == 1)
                {
                    printf("_");
                }
                if(j%2 == 0)
                {
                    printf("*");
                }
            }
        }
        printf("\n");
    }
    return 0;
}
