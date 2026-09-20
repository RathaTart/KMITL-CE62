#include <stdio.h>
#include <string.h>

int main()
{
    char long_string[100];
    char sub_string[100];
    char enter;
    int run;

    scanf("%[^\n]s", long_string);
    scanf("\n%[^\n]s", sub_string);
//    printf("%s\n", long_string);
//    printf("%s\n", sub_string);

    for(int i=0; i<strlen(long_string); i++)
    {
        int lenght = 0;
        printf("i = %d\n", i);
        for(int j=0; j<strlen(sub_string); j++)
        {
            if(long_string[i] != sub_string[j])
            {
                j = 101;
                printf("Not Match\n");
            }
            else
            {
                lenght++;

                printf("Lenght = %d\n", lenght);
            }

            if(strlen(sub_string) == lenght)
            {
                printf("%d\n", i);
            }
            else if(i==99)
            {
                printf("-1");
            }
        }
    }
    return 0;
}
