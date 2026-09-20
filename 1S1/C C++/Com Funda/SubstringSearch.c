#include <stdio.h>
#include <string.h>

int main()
{
    char str[100], sub[100];

    scanf("%[^\n]%*c", str);
    scanf("%[^\n]%*c", sub);

//    printf("STR = %s\n", str);
//    printf("SUB = %s\n", sub);
//    printf("lenSub = %d\n", strlen(sub));

    int count = 0;
    int found = 0;
    int num = 0;
    for(int i=0; i<strlen(str); i++)
    {
        while(str[i] == sub[count])
        {
            count++;
            if(count == strlen(sub))
            {
                printf("%d", i);
                found = 1;
            }
        }
    }
    if(found == 0)
    {
        printf("-1");
    }

    return 0;
}

// no space
