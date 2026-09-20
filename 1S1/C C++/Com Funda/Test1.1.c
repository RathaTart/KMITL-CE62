#include <stdio.h>

int main()
{
    int a[3];

    scanf("%d %d %d", &a[0], &a[1], &a[2]);

    //sort
    for(int i=0; i<3; i++)
    {
        for(int j=0; j<3; j++)
        {
            int temp = 0;
            if(a[i]<a[j])
            {
                temp = a[i];
                a[i] = a[j];
                a[j] = temp;
            }
        }
    }

    //check side
    if( (a[0]+a[1]) > a[2] )
    {
        printf("Yes");
    }
    else
    {
        printf("No");
    }


    return 0;
}
