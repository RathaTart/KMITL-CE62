
#include <stdio.h>
#include <stdbool.h>

bool uniq(char *p_str1, char *p_str2)
{
    while( *p_str1 != '\0')
    {
        if(*p_str1 != *p_str2)
        {
            return false;
        }

        do{ p_str1++;
        } while(*p_str1 == *(p_str1-1));

        do{ p_str2++;
        } while(*p_str2 == *(p_str2-1));

        if((*p_str1 == '\0'&&(*p_str2 == '\0')))
        {
            return true;
        }
    }
}


int main()
{
    char str1[100], str2[100];
    char *p_str1, *p_str2;

    scanf("%s", str1);
    scanf("%s", str2);

    p_str1 = str1;
    p_str2 = str2;

    if( uniq(p_str1,p_str2) == true )
    {
        printf("Same\n");
    }
    else{ printf("Difference\n"); }


    return 0;
}
