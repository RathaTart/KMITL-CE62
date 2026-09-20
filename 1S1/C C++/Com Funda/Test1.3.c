#include <stdio.h>

int main()
{
    int num1, num2;

    scanf("%d %d", &num1, &num2);

    for(int i=num1+1; i<num2; i++)
    {
        if( (i%num1 == 0) && (num2%i == 0) )
        {
            printf("%d ", i);
        }
    }

    return 0;
}
