
#include<stdio.h>
#include<string.h>
#include<math.h>

int main()
{
    char str[100];
    int dec = 0;
    scanf("%s", str);
    for(int i=0; i<strlen(str); i++)
    {
        if(str[i] <  58)
        {
            int temp = str[i] - 48;
            dec = temp * pow(16, strlen(str)-i-1) + dec;
        }
        else
        {
            int temp = str[i] - 55;
            dec = temp * pow(16, strlen(str)-i-1) + dec;
        }
    }

    printf("Dec = %d", dec);

    return 0;
}
