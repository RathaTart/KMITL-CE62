#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
#include <conio.h>
#include <stdbool.h>

#define SCREEN_WIDTH 110
#define SCREEN_HEIGHT 20

char cursor(int x, int y)
{
    HANDLE hStd = GetStdHandle(STD_OUTPUT_HANDLE);
    char buf[2]; COORD c = {x,y}; DWORD num_read;
    if(
    !ReadConsoleOutputCharacter(hStd,(LPTSTR)buf,1,c,(LPDWORD)&num_read) )
        return '\0';
    else
        return buf[0];
}

void draw_score(int x, int y, int score)
{
    gotoxy(x,y);
    setcolor(5,0);
    printf("SCORE = %d", score);
}

void setcolor(int fg,int bg)
{
    HANDLE hConsole = GetStdHandle(STD_OUTPUT_HANDLE);
    SetConsoleTextAttribute(hConsole, bg*16+fg);
}

void setcursor(bool visible)
{
    HANDLE console = GetStdHandle(STD_OUTPUT_HANDLE);
    CONSOLE_CURSOR_INFO lpCursor;
    lpCursor.bVisible = visible;
    lpCursor.dwSize = 20;
    SetConsoleCursorInfo(console,&lpCursor);
}

void gotoxy(int x, int y)
{
    COORD c = { x, y };
    SetConsoleCursorPosition(
    GetStdHandle(STD_OUTPUT_HANDLE) , c);
}

void erase_ship(int x,int y)
{
    gotoxy(x,y);
    setcolor(0,0);
    printf("          \n");
    gotoxy(x,y+1);
    printf("          \n");
    gotoxy(x,y+2);
    printf("          \n");
    gotoxy(x,y+3);
    printf("          \n");
}

void draw_ship(int x,int y)
{
    int color_ship = 2;
    int color_background = 4;

    gotoxy(x,y);
    setcolor(0,0);
    printf("   ");
    setcolor(color_ship,color_background);
    printf("T");
    setcolor(0,0);
    printf("   \n");
    gotoxy(x,y+1);
    setcolor(0,0);
    printf("  ");
    setcolor(color_ship,color_background);
    printf("AAA");
    setcolor(0,0);
    printf("  \n");
    gotoxy(x,y+2);
    setcolor(0,0);
    printf(" ");
    setcolor(color_ship,color_background);
    printf("RRRRR");
    setcolor(0,0);
    printf(" \n");
    gotoxy(x,y+3);
    setcolor(color_ship,color_background);
    printf("TTTTTTT\n");
}

void erase_bullet(int x,int y)
{
    gotoxy(x,y);
    setcolor(0,0);
    printf(" \n");
    printf("  ");
}

void draw_bullet(int x,int y)
{
    int color_bullet = 7;
    int color_background = 7;

    gotoxy(x,y);
    setcolor(color_bullet,color_background);
    printf(" ");
}

void erase_star(int x,int y)
{
    gotoxy(x,y);
    setcolor(0,0);
    printf(" \n");
}

void draw_star(int x,int y)
{
    int color_bullet = 10;
    int color_background = 0;

    gotoxy(x,y);
    setcolor(color_bullet,color_background);
    printf("*");
}

int main()
{
    char ch=' ';
    int x=SCREEN_WIDTH/2,y=SCREEN_HEIGHT/2;
    const int not_moving = 0, left = 1, right = 2, up = 3, down = 4;
    int direction_ship = not_moving;
    const bool OFF = false, ON = true;
    int bullet_capacity = 5;
    int bullet_slot = 0;
    bool bullet_status[5] = {OFF, OFF, OFF, OFF, OFF};
    int bullet_direction_x[bullet_capacity], bullet_direction_y[bullet_capacity];
    int bullet_count = 0;
    int number_star = 20;
    int score = 0;

    setcursor(0);
    draw_ship(x,y);
    draw_score(100,1,score);

    srand( time( NULL ) );
    for(int i=1; i<=number_star; i++)
    {
        int num1 = (rand()%61)+10;
        int num2 = (rand()%3)+2;

        if(cursor(num1,num2) != '*')
        {
            draw_star(num1,num2);
        }
    }

    do
    {
        if(_kbhit())
        {
            ch = _getch();
            if(ch == 'a') {direction_ship = left;}
            if(ch == 'd') {direction_ship = right;}
            if(ch == 'w') {direction_ship = up;}
            if(ch == 's') {direction_ship = down;}
            if(ch == ' ')
            {
                //Beep(1000,100);
                if(bullet_status[bullet_slot] == ON)
                {
                    //Don't do anything.
                }
                else
                {
                    bullet_status[bullet_slot] = ON;
                    bullet_direction_x[bullet_slot] = x+3;
                    bullet_direction_y[bullet_slot] = y-2;
                    bullet_slot = (bullet_slot+1)%bullet_capacity;
                    bullet_count++;
                }
            }
        }
        if((direction_ship == left)&&(x>0)) {erase_ship(x,y); draw_ship(--x,y);}
        if((direction_ship == right)&&(x<SCREEN_WIDTH)) {erase_ship(x,y); draw_ship(++x,y);}
        if((direction_ship == up)&&(y>5)) {erase_ship(x,y); draw_ship(x,--y);}
        if((direction_ship == down)&&(y<SCREEN_HEIGHT)) {erase_ship(x,y); draw_ship(x,++y);}

        for(int i=0; i<bullet_capacity; i++)
        {
            //Beep(700,100);
            if(cursor(bullet_direction_x[i], bullet_direction_y[i]-1) == '*')
            {
                //Beep(400,100);

                score += 10;
                draw_score(100,1,score);

                int num1 = (rand()%61)+10;
                int num2 = (rand()%3)+2;

                if(cursor(num1,num2) != '*')
                {
                    draw_star(num1,num2);
                }
            }

            gotoxy(0,0);
            setcolor(10,0);
            //printf("CURSOR = %c\n", cursor(bullet_direction_x[i], bullet_direction_y[i]));

            erase_bullet(bullet_direction_x[i],bullet_direction_y[i]);
            if((bullet_status[i] == ON) && (bullet_direction_y[i] > 0) && (bullet_count <= bullet_capacity))
            {
                draw_bullet(bullet_direction_x[i], --bullet_direction_y[i]);
            }
            else
            {
                bullet_status[i] = OFF;
                bullet_count--;
            }
        }
        fflush(stdin);
    Sleep(1);
    } while (ch!='x');

    return 0;
}
