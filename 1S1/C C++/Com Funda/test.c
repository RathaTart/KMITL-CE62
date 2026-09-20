#include <stdio.h>
#include <windows.h>
#include <time.h>

#define scount 80
#define screen_x 80
#define screen_y 25

HANDLE wHnd;
CHAR_INFO consoleBuffer[screen_x * screen_y];
COORD bufferSize = { screen_x,screen_y };
COORD characterPos = { 0,0 };
SMALL_RECT windowSize = { 0,0,screen_x-1,screen_y-1 };
COORD star[scount];

int setConsole(int x, int y)
{
    wHnd = GetStdHandle(STD_OUTPUT_HANDLE);
    SetConsoleWindowInfo(wHnd, TRUE, &windowSize);
    SetConsoleScreenBufferSize(wHnd, bufferSize);
    return 0;
}

void clear_buffer()
{
    for (int y = 0; y < screen_y; ++y)
    {
        for (int x = 0; x < screen_x; ++x)
        {
            consoleBuffer[x + screen_x * y].Char.AsciiChar = ' ';
            consoleBuffer[x + screen_x * y].Attributes = 7;
        }
    }
}

void init_star()
{
    for(int i = 0; i< scount; i++)
    {
        star[i].X = (SHORT)(rand() % screen_x);
        star[i].Y = (SHORT)(rand() % screen_y);
    }
}

void star_fall()
{
    int i;
    for (i = 0; i < scount; i++)
    {
        if (star[i].Y >= screen_y-1)
        {
            star[i].X = rand()%screen_x;
            star[i].Y = 1;
        }
        else
        {
            star[i] = { star[i].X,star[i].Y+1 };
        }
    }

void fill_star_to_buffer()
{
    for(int i=0; i < scount; i++)
    {
        consoleBuffer[star[i].X + screen_x * star[i].Y].Char.AsciiChar = '*';
        consoleBuffer[star[i].X + screen_x * star[i].Y].Attributes = 7;
    }
}

void fill_buffer_to_console()
{
    WriteConsoleOutputA(wHnd, consoleBuffer, bufferSize, characterPos,
                        &windowSize);
}

int main()
{
    srand( time( NULL ) );
    setConsole(screen_x, screen_y);

    init_star();
    i = 0;
    while (i < 1000)
    {
        star_fall();
        clear_buffer();
        fill_star_to_buffer();
        fill_buffer_to_console();
        Sleep(200);
        i++;
    }
    fill_data_to_buffer();
    fill_buffer_to_console();
    Sleep(5000);
    return 0;
}
