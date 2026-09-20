
#include <stdio.h>


int main()
{
    char str1[100], str2[100];
    char *p_str1, *p_str2;

    scanf("%s", str);
    p = str;

    while( *p != '\0')
    {
        if( (*p >= 'A') && (*p <= 'Z'))
        {
            printf("%c", *p+32);
        }
        else if( (*p >= 'a') && (*p <= 'z') )
        {
            printf("%c", *p-32);
        }
        p++;
    }

    return 0;
}
