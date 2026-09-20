#include <stdio.h>
#include <windows.h>
#include <time.h>

#define scount 80
#define screen_x 80
#define screen_y 25

HANDLE wHnd;
HANDLE rHnd;
DWORD fdwMode;
DWORD numEvents = 0;
DWORD numEventsRead = 0;
CHAR_INFO consoleBuffer[screen_x * screen_y];
int speed = 100;
int life = 10;
int max_color = 15;

COORD bufferSize = { screen_x,screen_y};
COORD characterPos = { 0,0 };
SMALL_RECT windowSize = { 0,0,screen_x,screen_y};
COORD star[scount];


int setMode()
{
    rHnd = GetStdHandle(STD_INPUT_HANDLE);
    fdwMode = ENABLE_EXTENDED_FLAGS | ENABLE_WINDOW_INPUT |
              ENABLE_MOUSE_INPUT;
    SetConsoleMode(rHnd, fdwMode);
    return 0;
}

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
        star[i].X = (rand() % screen_x);
        star[i].Y = (rand() % screen_y);
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

void draw_ship(int x,int y, int color_ship)
{
    consoleBuffer[x-1 + screen_x * y].Char.AsciiChar = '<';
    consoleBuffer[x-1 + screen_x * y].Attributes = color_ship;
    consoleBuffer[x + screen_x * y].Char.AsciiChar = '0';
    consoleBuffer[x + screen_x * y].Attributes = color_ship;
    consoleBuffer[x+1 + screen_x * y].Char.AsciiChar = '>';
    consoleBuffer[x+1 + screen_x * y].Attributes = color_ship;
}

int main()
{
    srand( time( NULL ) );
    setConsole(screen_x, screen_y);

    int i=0;
    bool play = true;
    DWORD numEvents = 0;
    DWORD numEventsRead = 0;
    int old_X_location = 0;
    int old_Y_location = 0;
    int ship_color = 7;

    setConsole(screen_x, screen_y);
    setMode();
    init_star();
    clear_buffer();

    while (play)
    {
        fill_star_to_buffer();
        star_fall();

        if(life <= 0)
        {
            play = false;
            break;
        }

        GetNumberOfConsoleInputEvents(rHnd, &numEvents);
        if (numEvents != 0)
        {
            INPUT_RECORD* eventBuffer = new INPUT_RECORD[numEvents];
            ReadConsoleInput(rHnd, eventBuffer, numEvents, &numEventsRead);

            for (DWORD i = 0; i < numEventsRead; ++i)
            {

                if (eventBuffer[i].Event.KeyEvent.wVirtualKeyCode == VK_ESCAPE)
                {
                    play = false;
                    break;
                }
                if (eventBuffer[i].Event.KeyEvent.uChar.AsciiChar == 'c')
                {
                    ship_color = rand()%max_color+1;
                }

                if (eventBuffer[i].EventType == MOUSE_EVENT)
                {
                    int posx = eventBuffer[i].Event.MouseEvent.dwMousePosition.X;
                    int posy = eventBuffer[i].Event.MouseEvent.dwMousePosition.Y;
                    old_X_location = posx;
                    old_Y_location = posy;

                    if (eventBuffer[i].Event.MouseEvent.dwButtonState &
                            FROM_LEFT_1ST_BUTTON_PRESSED)
                    {
                        ship_color = rand()%max_color+1;
                    }
                    draw_ship(posx, posy, ship_color);
                }
            }

            for (int num_star = 0; num_star < scount; num_star++)
            {
                if((star[num_star].X == old_X_location) && (star[num_star].Y == old_Y_location))
                {
                    life--;
                    star[num_star].X = rand() % screen_x;
                    star[num_star].Y = 1;
                }
                else if((star[num_star].X == old_X_location-1) && (star[num_star].Y == old_Y_location))
                {
                    life--;
                    star[num_star].X = rand() % screen_x;
                    star[num_star].Y = 1;
                }
                else if((star[num_star].X == old_X_location+1) && (star[num_star].Y == old_Y_location))
                {
                    life--;
                    star[num_star].X = rand() % screen_x;
                    star[num_star].Y = 1;
                }
            }
            delete[] eventBuffer;
        }
        else
        {
            for (int num_star = 0; num_star < scount; num_star++)
            {
                if((star[num_star].X == old_X_location) && (star[num_star].Y == old_Y_location))
                {
                    life--;
                    star[num_star].X = rand() % screen_x;
                    star[num_star].Y = 1;
                }
                else if((star[num_star].X == old_X_location-1) && (star[num_star].Y == old_Y_location))
                {
                    life--;
                    star[num_star].X = rand() % screen_x;
                    star[num_star].Y = 1;
                }
                else if((star[num_star].X == old_X_location+1) && (star[num_star].Y == old_Y_location))
                {
                    life--;
                    star[num_star].X = rand() % screen_x;
                    star[num_star].Y = 1;
                }
            }
            draw_ship(old_X_location, old_Y_location, ship_color);
        }

        fill_buffer_to_console();
        clear_buffer();


        Sleep(speed);
    }

    return 0;
}
