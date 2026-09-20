#include<stdio.h>

int main()
{
    char input[1000];
    int count;
    scanf("%s", &input);

    for(count=0; input[count] != '\0' ; count++);
//    printf("Count = %d", count);

     if(count==1)
     {
         printf("No Output");
     }

     if(count>1)
     {
        for(int i=0; i<count; i++)
        {
            for (int j=0; j<count-i-1; j++)
            {
                printf("%c", input[j]);
            }
            printf("\n");
        }
     }


    return 0;
}
