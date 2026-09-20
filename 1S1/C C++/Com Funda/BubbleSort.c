#include <stdio.h>

int bubble_sort(int arr[])
{
    int trans1, trans2;
    for(int j=0; j<9; j++)
    {
        for (int i=0; i<9; i++)
        {
          if(arr[i]>arr[i+1])
          {
              trans1 = arr[i];
              trans2 = arr[i+1];
              arr[i] = trans2;
              arr[i+1] = trans1;
          }
        }
    }
    return arr;
}

int main()
{
    int arr[10];
    for(int i=0; i<10; i++)
    {
        scanf("%d ", &arr[i]);
    }

    int arr2[10] = bubble_sort(arr);
     for(int i=0; i<10; i++)
    {
        printf("%d ", arr[i]);
    }

}

