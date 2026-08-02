using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;
using System.Text.RegularExpressions;

class TestWeather
{
    static string HttpGetUtf8(string url, string referer)
    {
        using (WebClient wc = new WebClient())
        {
            wc.Encoding = Encoding.UTF8;
            wc.Headers[HttpRequestHeader.UserAgent] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)";
            if (!string.IsNullOrEmpty(referer))
                wc.Headers[HttpRequestHeader.Referer] = referer;
            return wc.DownloadString(url);
        }
    }

    static string ParseWeather(string page, string fallbackName)
    {
        string name = Regex.Match(page, "\"city\":\"([^\"]+)\"").Groups[1].Value;
        if (string.IsNullOrEmpty(name)) name = fallbackName;
        string tHigh = Regex.Match(page, "\"temp\":\"([^\"]+)\"").Groups[1].Value;
        string tLow = Regex.Match(page, "\"tempn\":\"([^\"]+)\"").Groups[1].Value;
        string weather = Regex.Match(page, "\"weather\":\"([^\"]+)\"").Groups[1].Value;
        int i = page.IndexOf("var dataSK");
        string sk = i >= 0 ? page.Substring(i) : page;
        string rt = Regex.Match(sk, "\"temp\":\"([^\"]+)\"").Groups[1].Value;
        string wd = Regex.Match(sk, "\"WD\":\"([^\"]+)\"").Groups[1].Value;
        string ws = Regex.Match(sk, "\"WS\":\"([^\"]+)\"").Groups[1].Value;
        string sd = Regex.Match(sk, "\"SD\":\"([^\"]+)\"").Groups[1].Value;
        string rw = Regex.Match(sk, "\"weather\":\"([^\"]+)\"").Groups[1].Value;
        if (string.IsNullOrEmpty(weather)) weather = rw;
        if (string.IsNullOrEmpty(weather)) weather = "天气数据获取中";
        string line1 = "主人～今日天气播报！";
        string line2 = name + "：" + weather;
        string line3 = "";
        if (!string.IsNullOrEmpty(tHigh) && tHigh != "999")
            line3 = "气温 " + tLow + "℃~" + tHigh + "℃";
        else if (!string.IsNullOrEmpty(tLow))
            line3 = "气温约 " + tLow + "℃";
        if (!string.IsNullOrEmpty(rt) && rt != "999")
            line3 = line3.Length > 0 ? line3 + "　实时" + rt + "℃" : "实时温度 " + rt + "℃";
        string line4 = "";
        if (!string.IsNullOrEmpty(wd) || !string.IsNullOrEmpty(ws))
            line4 = (wd + " " + ws).Trim();
        if (!string.IsNullOrEmpty(sd)) line4 = line4.Length > 0 ? line4 + " · 湿度" + sd : "湿度 " + sd;
        return line1 + "\n" + line2 + (line3.Length > 0 ? "\n" + line3 : "") + (line4.Length > 0 ? "\n" + line4 : "");
    }

    static string NormalizeCity(string city)
    {
        string s = city;
        string[] suf = { "特别行政区", "维吾尔自治区", "壮族自治区", "回族自治区", "自治区", "自治州", "自治县", "地区", "省", "市", "盟", "县" };
        foreach (string t in suf)
        {
            if (s.EndsWith(t)) { s = s.Substring(0, s.Length - t.Length); break; }
        }
        return s.Trim();
    }

    static Dictionary<string, string> CityCodes = new Dictionary<string, string>()
    {
        { "北京", "101010100" }, { "上海", "101020100" }, { "天津", "101030100" }, { "重庆", "101040100" },
        { "哈尔滨", "101050101" }, { "广州", "101280101" }, { "深圳", "101280601" }, { "成都", "101270101" },
        { "武汉", "101200101" }, { "杭州", "101210101" },
    };

    static string CityNameToCode(string name)
    {
        if (string.IsNullOrEmpty(name)) return "";
        if (CityCodes.ContainsKey(name)) return CityCodes[name];
        foreach (KeyValuePair<string, string> kv in CityCodes)
        {
            if (kv.Key.Contains(name) || name.Contains(kv.Key)) return kv.Value;
        }
        return "";
    }

    static string CityCodeSearch(string name)
    {
        try
        {
            string s = HttpGetUtf8("http://toy1.weather.com.cn/search?cityname=" + Uri.EscapeDataString(name), "http://www.weather.com.cn/");
            Match m = Regex.Match(s, "\"ref\"\\s*:\\s*\"(\\d+)");
            if (m.Success) return m.Groups[1].Value;
        }
        catch (Exception e) { Console.WriteLine("search fail: " + e.Message); }
        return "";
    }

    static void Main()
    {
        Console.OutputEncoding = Encoding.UTF8;
        Console.WriteLine("== NormalizeCity ==");
        foreach (string c in new[] { "北京市", "广州市", "内蒙古自治区", "湘西土家族苗族自治州", "香港特别行政区", "东莞市" })
            Console.WriteLine("  " + c + " -> " + NormalizeCity(c));

        Console.WriteLine("== CityNameToCode ==");
        Console.WriteLine("  北京 -> " + CityNameToCode("北京"));
        Console.WriteLine("  深圳市 -> " + CityNameToCode("深圳"));

        Console.WriteLine("== CityCodeSearch ==");
        Console.WriteLine("  广州 -> " + CityCodeSearch("广州"));

        Console.WriteLine("== ParseWeather 北京 ==");
        try
        {
            string page = HttpGetUtf8("http://d1.weather.com.cn/weather_index/101010100.html", "http://www.weather.com.cn/");
            Console.WriteLine(ParseWeather(page, "北京"));
        }
        catch (Exception e) { Console.WriteLine("fetch fail: " + e.Message); }

        Console.WriteLine("== ParseWeather 广州 ==");
        try
        {
            string page = HttpGetUtf8("http://d1.weather.com.cn/weather_index/101280101.html", "http://www.weather.com.cn/");
            Console.WriteLine(ParseWeather(page, "广州"));
        }
        catch (Exception e) { Console.WriteLine("fetch fail: " + e.Message); }

        Console.WriteLine("== IP 定位 ==");
        try
        {
            string s = HttpGetUtf8("http://pv.sohu.com/cityjson", null);
            Console.WriteLine("  sohu: " + s);
        }
        catch (Exception e) { Console.WriteLine("  sohu fail: " + e.Message); }
        try
        {
            string j = HttpGetUtf8("http://ip-api.com/json/?lang=zh-CN&fields=status,city", null);
            Console.WriteLine("  ip-api: " + j);
        }
        catch (Exception e) { Console.WriteLine("  ip-api fail: " + e.Message); }
    }
}
