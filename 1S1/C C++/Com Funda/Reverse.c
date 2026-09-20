#include <stdio.h>
#include <string.h>

int main(void)
{
    char str[100], reverse[100];
    scanf("%[^\n]%*c", str);
    int len = strlen(str);

    int word = 1;
    for(int i=0; i<len; i++)
    {
        if(str[i] == ' ')
        {
            word++;
        }
    }

    char *p1, *p2;
    p1 = &str[len-1];

    int count = 0;
    int wordLoop = 1;
    for(int i=0; i<len; i++)
    {
        if(*p1 != ' ' && wordLoop != word)
        {
            p1--;
        }
        else
        {
            if(wordLoop == word)
            {
                p2 = &str[0];
                while(*p2 != ' ')
                {
                    reverse[count] = *p2;
                    p2++;
                    count++;
                    reverse[count] = '\0';
                }
                break;
            }
            p2 = p1+1;
            while((*p2 != ' ') && (*p2 != '\0'))
            {
                reverse[count] = *p2;
                count++;
                p2++;
            }
            reverse[count] = ' ';
            count++;
            p1--;
            wordLoop++;
        }
    }

    printf("%s", reverse);

    return 0;
}
