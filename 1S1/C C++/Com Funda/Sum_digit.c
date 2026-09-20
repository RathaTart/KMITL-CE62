
#include <stdio.h>

int main()
{
    int n;
    scanf("%d", &n);
    int sum = 0;
    for(;;)
    {
        if(n>0)
        {
            sum = sum + n%10;
            n = n/10;
        }
        else if(n<10)
        {
            n = sum;
            sum = 0;
        }
        if((n==0)&&(sum<10))
        {
            printf("%d", sum);
            break;
        }
    }

    return 0;
}
