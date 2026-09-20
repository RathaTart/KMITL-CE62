#include<stdio.h>

int main()
{
    int str[30];
    int A, B;
    char C;
    int Year, Mon, Day, Hr, Min, Sec, Mili;
    scanf("%d.%d.%d.%d.%d.%d.%d", &Year, &Mon, &Day, &Hr, &Min, &Sec, &Mili);
    //printf("%d.%d.%d.%d.%d.%d.%d", Year, Mon, Day, Hr, Min, Sec, Mili);

    A = Year*Mon*Sec;
    B = (Hr+Mili)*Sec;
    if (Day*Mili > 1500)
    {
        C = 'A';
    }
    else
    {
        C = 'B';
    }

    printf("%d%d%c", A,B,C);

    return 0;
}
