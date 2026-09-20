#include <stdio.h>
#include <string.h>

int main()
{
    char main[100], sub[100];
    scanf("%[^\n]%*c", main);
    scanf("%[^\n]%*c", sub);

//    printf("MAIN = %s\n", main);
//    printf("SUB = %s\n", sub);
//    printf("Size = %d\n", strlen(main));


    int count = 0;
    int found = 0;
    int temp = 0;
    int first = 1;
    int space_count = 0;
    int sub_count = 0;

    for(int i=0; i<strlen(main); i++)
    {
//        printf("Loop%d\n", i);
        if(main[i] == ' ')
        {
            space_count++;
        }
        if(main[i] != sub[sub_count] && first == 0)
        {
            sub_count = 0;
            count = 0;
            first = 1;
            i = temp;
        }
        else if(main[i] == sub[sub_count])
        {
//            printf("FoundLoop%d\n", i);
//            printf("main[%d] = %c\n", i, main[i]);
//            printf("sub[%d] = %c\n", sub_count, sub[sub_count]);
            if(first)
            {
                temp = i;
                first = 0;
            }
            sub_count++;
            count++;

            if(count == strlen(sub))
            {
                found = 1;
                printf("%d\n", temp);
                break;
            }
        }
    }

    if(!found)
    {
        printf("-1");
    }

    return 0;
}
