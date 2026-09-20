#include <stdio.h>
#include <windows.h>
#include <conio.h>

#define SCREEN_WIDTH 80
#define SCREEN_HEIGHT 25

void gotoxy(int x, int y)
{
    COORD c = {x, y};
    SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), c);
}

void draw_ship(int x, int y)
{
    gotoxy(x, y);
    printf("<-0->");
}

void erase_ship(int x, int y)
{
    gotoxy(x, y);
    printf("     ");
}

void draw_border()
{
    int i;
    for (i = 0; i <= SCREEN_WIDTH; i++)
    {
        gotoxy(i, 0);
        printf("#");
        gotoxy(i, SCREEN_HEIGHT);
        printf("#");
    }
    for (i = 1; i < SCREEN_HEIGHT; i++)
    {
        gotoxy(0, i);
        printf("#");
        gotoxy(SCREEN_WIDTH, i);
        printf("#");
    }
}

int main()
{
    char ch = ' ';
    int x = SCREEN_WIDTH / 2, y = SCREEN_HEIGHT / 2;
    draw_border();
    draw_ship(x, y);

    do
    {
        if (_kbhit())
        {
            ch = _getch();
            if (ch == 'a' && x > 1)
            {
                erase_ship(x, y);
                draw_ship(--x, y);
            }
            if (ch == 'd' && x < SCREEN_WIDTH - 6)
            {
                erase_ship(x, y);
                draw_ship(++x, y);
            }
            if (ch == 's' && y < SCREEN_HEIGHT - 1)
            {
                erase_ship(x, y);
                draw_ship(x, ++y);
            }
            if (ch == 'w' && y > 1)
            {
                erase_ship(x, y);
                draw_ship(x, --y);
            }
            fflush(stdin);
        }
        Sleep(1);
    } while (ch != 'x');

    return 0;
}
