#include<stdio.h>

int palindrome(char str[])
{
    int count=0;
//    printf("%s\n", str);
    for(int i=0;str[i] != '\0'; i++)
    {
        count++;
    }
//    printf("COUNT = %d", count);
    for(int j=0; j<count/2; j++)
    {
//        printf("%c\n", str[j]);
        if(str[j] != str[count-j-1])
        {
            return 0;
        }
    }
    return 1;
}

int main()
{
    char str[21];
    int resulth;
    scanf("%s", &str);
//    printf("%s\n", str);
    resulth = palindrome(str);
    if(resulth == 1)
    {
        printf("%s is palindrome", str);
    }
    else if(resulth == 0)
    {
        printf("%s is  not palindrome", str);
    }
    return 0;
}
