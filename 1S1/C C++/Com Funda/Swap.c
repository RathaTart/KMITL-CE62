#include <stdio.h>

void swap(int *pa, int *pb)
{
    int temp;
    temp = *pa;
    *pa = *pb;
    *pb = temp;
}

int main()
{
    int a,b;
    int *pa, *pb;

    scanf("%d %d", &a, &b);
    pa = &a;
    pb = &b;

    swap(pa, pb);
    printf("%d %d", a, b);

    return 0;
}
