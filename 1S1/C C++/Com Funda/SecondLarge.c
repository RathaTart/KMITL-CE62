#include<stdio.h>

int cmpfunc (const void * a, const void * b) {
   return ( *(int*)a - *(int*)b );
}

int main()
{
    int arr[8];
    for(int i=0; i<7; i++)
    {
        scanf("%d, ", &arr[i]);
    }
    scanf("%d", &arr[7]);

    qsort(arr, 8, sizeof(int), cmpfunc);

    printf("%d", arr[6]);

    return 0;
}

