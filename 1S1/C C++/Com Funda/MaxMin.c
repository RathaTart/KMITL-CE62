#include <stdio.h>

int main(void)
{
    int min, max;
    int str[5];
    int trans1, trans2;
    scanf("%d %d %d %d %d", &str[0], &str[1], &str[2], &str[3], &str[4]);
//    printf("%d\n", str[4]);
//    printf("%d\n", str[5]);
    for(int j=0; j<4; j++)
    {
        for (int i=0; i<4; i++)
        {
          if(str[i]>str[i+1])
          {
              trans1 = str[i];
              trans2 = str[i+1];
              str[i] = trans2;
              str[i+1] = trans1;
          }
        }
    }
//    for(int i=0; i<5; i++)
//    {
//        printf("%d\n", str[i]);
//    }

    printf("%d %d", str[0], str[4]);

    // printf("%d %d", min, max);
    return 0;
}

// 1 4 7 6 3
