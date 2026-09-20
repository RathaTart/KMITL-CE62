
#include <stdio.h>

int main()
{
    int sum = 0;
    for(int i=2; i<=10000; i++)
    {
        for(int j=1; j<=i/2; j++)
        {
            if(i%j==0)
            {
                sum = sum + j;
            }
            if((j==i/2)&&(sum==i))
            {
                printf("%d\n", i);
            }
        }
        sum = 0;
    }
    return 0;
}
