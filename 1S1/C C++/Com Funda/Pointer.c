#include<stdio.h>

int main()
{
//    int p = 25;
//    int m;
//    m = ++p;
//    printf("p = %d\n", m);
//    printf("p = %d", p);

    int A =25;
    int *ptr = &A;
    ptr++;
    printf("Ptr = %d\n", *ptr);


    return 0;
}
