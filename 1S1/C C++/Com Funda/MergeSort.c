#include <stdio.h>
#include <string.h>

int main()
{
    char str1[100] = {'0'}, str2[100];

    scanf("%[^\n]%*c", str1);
    scanf("%[^\n]%*c", str2);

    int count1 = 1, count2 = 1;
    for(int i=0; i<strlen(str1); i++)
    {
        if(str1[i] == ' ')
        {
            count1++;
        }
    }
    //printf("C1 = %d\n", count1);

    for(int i=0; i<strlen(str2); i++)
    {
        if(str2[i] == ' ')
        {
            count2++;
        }
    }
    //printf("C2 = %d\n", count2);

    int arr1[count1];
    int arr2[count2];
    memset(arr1, 0, sizeof(arr1));
    memset(arr2, 0, sizeof(arr2));
    int count3 = count1 + count2;
    int arr3[count3];

    int count = 0;
    for(int i=0; i<strlen(str1); i++)
    {
        if(str1[i] == ' ')
        {
            count++;
        }
        else
        {
            arr1[count] = arr1[count] * 10 + (str1[i] - 48);
        }
    }

    count = 0;
    for(int i=0; i<strlen(str2); i++)
    {
        if(str2[i] == ' ')
        {
            count++;
        }
        else
        {
            arr2[count] = arr2[count] * 10 + (str2[i] - 48);
        }
    }

    int num = 0;
    for(int i=0; i<count1; i++)
    {
        arr3[num] = arr1[i];
        num++;
    }
    for(int i=0; i<count2; i++)
    {
        arr3[num] = arr2[i];
        num++;
    }

    for(int i=0; i<count3; i++)
    {
        for(int j=0; j<count3; j++)
        {
            if(arr3[i]<arr3[j])
            {
                int temp = arr3[i];
                arr3[i] = arr3[j];
                arr3[j] = temp;
            }
        }
    }

//    printf("%s\n", str1);
//    printf("%s\n", str2);
//
//    for(int i=0; i<count1; i++)
//    {
//        printf("%d ", arr1[i]);
//    }
//    printf("\n");
//
//    for(int i=0; i<count2; i++)
//    {
//        printf("%d ", arr2[i]);
//    }
//    printf("\n");

    for(int i=0; i<count3; i++)
    {
        printf("%d ", arr3[i]);
    }
    printf("\n");


    return 0;
}
