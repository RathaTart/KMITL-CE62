#include<stdio.h>
#include<stdlib.h>
#include <windows.h>
#include<conio.h>

#define SCREEN_WIDTH 110
#define SCREEN_HEIGHT 25

void gotoxy(int x, int y)
{
    COORD c = { x, y };
    SetConsoleCursorPosition(
    GetStdHandle(STD_OUTPUT_HANDLE) , c);
}

void erase_ship(int x,int y)
{
    gotoxy(x,y);
    printf("       \n");
    gotoxy(x,y+1);
    printf("       \n");
    gotoxy(x,y+2);
    printf("       \n");
    gotoxy(x,y+3);
    printf("       \n");
}

void draw_ship(x,y)
{
    gotoxy(x,y);
    printf("   0   \n");
    gotoxy(x,y+1);
    printf("  -0-  \n");
    gotoxy(x,y+2);
    printf(" <-0-> \n");
    gotoxy(x,y+3);
    printf("<<-0->>\n");
}

int main()
{
    char ch=' ';
    int x=SCREEN_WIDTH/2,y=SCREEN_HEIGHT/2;
    draw_ship(x,y);
    do
    {
        if (_kbhit())
        {
            ch=_getch();
            if((ch=='a')&&(x>0)) {erase_ship(x,y); draw_ship(--x,y);}
            if((ch=='d')&&(x<SCREEN_WIDTH)) {erase_ship(x,y); draw_ship(++x,y);}
            if((ch=='w')&&(y>0)) {erase_ship(x,y); draw_ship(x,--y);}
            if((ch=='s')&&(y<SCREEN_HEIGHT)) {erase_ship(x,y); draw_ship(x,++y);}
            fflush(stdin);
        }
    Sleep(1);
    } while (ch!='x');

    return 0;
}
