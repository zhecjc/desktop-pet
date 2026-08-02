using System;
using System.IO;
using System.Windows.Forms;
namespace DesktopPet
{
    public static class TestMain
    {
        [STAThread]
        public static void Main()
        {
            string log = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "diag.log");
            try
            {
                File.AppendAllText(log, "step1 start\n");
                Native.SetProcessDPIAware();
                File.AppendAllText(log, "step2 dpi ok\n");
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                File.AppendAllText(log, "step3 styles ok\n");
                PetForm f = new PetForm();
                File.AppendAllText(log, "step4 form constructed\n");
                Application.Run(f);
                File.AppendAllText(log, "step5 run ended\n");
            }
            catch (Exception ex)
            {
                File.AppendAllText(log, "EXCEPTION: " + ex.ToString() + "\n");
            }
        }
    }
}
