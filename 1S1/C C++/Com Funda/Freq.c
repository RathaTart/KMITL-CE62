#include<stdio.h>

int cmpfunc (const void * a, const void * b) {
   return ( *(int*)a - *(int*)b );
}

int main()
{
    int arr[10];
    for(int i=0; i<9; i++)
    {
        scanf("%d, ", &arr[i]);
    }
    scanf("%d", &arr[9]);

    qsort(arr, 10, sizeof(int), cmpfunc);

//    for(int n = 0 ; n < 10; n++ )
//    {
//        printf("%d ", arr[n]);
//    }

    int freq=1;

    for(int i=0; i<10; i++)
    {
        if(arr[i]==arr[i+1])
        {
            freq++;
        }
        else
        {
            printf("Element %d: Frequency = %d\n", arr[i], freq);
            freq=1;
        }
    }
    return 0;
}
