#include <stdio.h>
#include <time.h>

int main()
{
    srand( time( NULL ) );
    int number = 5;

    for(int i=0; i<number; i++)
    {
        int symbol = rand()%2;
        printf("%d ", rand()%90+10);
        if(symbol == 0){ printf("+"); }
        else{ printf("-"); }
        printf(" %d = \n", rand()%90+10);
    }
    return 0;
}
