// // Case Study 01 - Multithreading (Refactored to use ThreadWork())
// // Updated: 2025-06-25
// using System;
// using System.IO;
// using CalculatingFunctions;
// using System.Threading;
// using System.Diagnostics;

// class Program
// {
//     // เก็บข้อมูลทั้งหมดไว้ที่นี่
//     static decimal[] data = new decimal[11_000_001];

//     // -------- Core worker: ทำงานคำนวณช่วง [start, end) ซ้ำ repeats รอบ แล้วคืนผลรวม --------
//     // หมายเหตุ: ใช้ตัวแปรท้องถิ่นทั้งหมด (ไม่ใช้ index/result แบบ global)
//     private static decimal ThreadWork(decimal[] data, int start, int end, int repeats)
//     {
//         var CF = new CalClass();
//         decimal local = 0m;

//         for (int r = 0; r < repeats; r++)
//         {
//             int idxLocal = start;
//             while (idxLocal < end)
//             {
//                 // Calculate1 จะอัปเดต idxLocal (ref) และแก้ data[idxLocal] ภายในตามอัลกอริทึม
//                 local += CF.Calculate1(ref data, ref idxLocal);
//             }
//         }
//         return local;
//     }

//     private static void LoadData()
//     {
//         Console.WriteLine("Loading data...");
//         using var fs = new FileStream("data.bin", FileMode.Open, FileAccess.Read, FileShare.Read);
//         using var br = new BinaryReader(fs);

//         for (int i = 0; i < data.Length; i++)
//         {
//             float f = br.ReadSingle();
//             data[i] = (decimal)(f * 36);
//         }
//         Console.WriteLine("Data loaded successfully.\n");
//     }

//     private static void Main(string[] args)
//     {
//         LoadData();
//         Console.WriteLine("Calculation start ...");

//         int N = Math.Min(10_000_000, data.Length);  // ใช้เฉพาะ 10 ล้านแรกตามโจทย์
//         int repeats = 30;                            // ทำซ้ำ 30 รอบ
//         int workers = Math.Max(1, Environment.ProcessorCount); // หรือจะ fix ค่าเองก็ได้ เช่น 20

//         int chunk = (N + workers - 1) / workers;

//         decimal[] partial = new decimal[workers];
//         Thread[] threads = new Thread[workers];

//         var sw = Stopwatch.StartNew();

//         for (int t = 0; t < workers; t++)
//         {
//             int start = t * chunk;
//             int end = Math.Min(start + chunk, N);
//             int ti = t;

//             threads[t] = new Thread(() =>
//             {
//                 // ย้ายลอจิกงานจริงมาเรียกผ่าน ThreadWork()
//                 partial[ti] = ThreadWork(data, start, end, repeats);
//             });

//             threads[t].Start();
//         }

//         for (int t = 0; t < workers; t++)
//             threads[t].Join();

//         sw.Stop();

//         decimal result = 0m;
//         for (int t = 0; t < workers; t++)
//             result += partial[t];

//         Console.WriteLine($"Calculation finished in {sw.ElapsedMilliseconds} ms. Result: {result:F25}");
//     }
// }
