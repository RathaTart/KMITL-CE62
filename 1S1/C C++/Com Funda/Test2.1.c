#include <stdio.h>
#include <string.h>

int main()
{
    char str[100], sub[100] = {'\0'}, temp[100];
    scanf("%s", str);
    printf("%s\n", str);

    char *p, *q, *r;
    p = str;
    q = sub;
    r = temp;

    int key1 = 0, count1 = 0, count2 = 0, first = 1;
    for(int i=0; i<strlen(str); i++)
    {
        if(*p == 'a' || *p == 'e' || *p == 'i' || *p == 'o' || *p == 'u')
        {
            printf("FOUND \n");
            key1 = 1;
        }

        p++;

        if(key1 == 1 && *p != 'a' && *p != 'e' && *p != 'i' && *p != 'o' && *p != 'u' && first == 1)
        {
            *q = *p;
            q++;
            count1++;
            printf("%s\n", sub);
        }
        else if(key1 == 1 && *p != 'a' && *p != 'e' && *p != 'i' && *p != 'o' && *p != 'u' && first == 0)
        {

            *r = *p;
            r++;
            count2++;
        }
        else
        {
            key1 = 0;
            first = 0;
            printf("Flase\n");
        }


    }

    printf("SUB = %s", sub);
}
