
#include <stdio.h>

int main()
{
    char str[100];
    char *p_front, *p_back;


    scanf("%s", str);
    p_front = str;
    p_back = str;

    while( *p_back != '\0')
    {
        p_back++;
    }

    p_back--;

    do
    {
        printf("FRONT = %c\n", *p_front);
        printf("BACK = %c\n", *p_back);

        if(*p_back != *p_front)
        {
            printf("Not Palindrome\n");
            break;
        }

        p_front++;
        p_back--;

        if(p_front >= p_back)
        {
            printf("Palindrome\n");
        }

    } while(p_back >= p_front);

    return 0;
}
