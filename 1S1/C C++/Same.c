#include<stdio.h>

int main()
{
    int n, same;
    scanf("%d ", &n);
    char input[2*n];
    gets(input);
//    printf("%s", input);
    for(int i=0; i< 2*n; i+=2)
    {
        for(int j=0; j< 2*n; j+=2)
        {
//            printf("%c", input[i]);
            if((input[i] == input [j]) && (i != j))
            {
                printf("%c", input[i]);
                return 0;
            }
        }
    }

    return 0;
}
