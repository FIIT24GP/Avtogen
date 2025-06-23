using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Windows.Forms;

public partial class Form1 : Form
{
    public Form1()
    {
        InitializeComponent();
    }

    private void ListBox_SelectedIndexChanged(object sender, EventArgs e)
    {
        if (ListBox.SelectedItem == null) return;

        string selectedProject = ListBox.SelectedItem.ToString();
        string avtogenPath = Path.Combine(Application.StartupPath, selectedProject + ".avtogen");

        if (!File.Exists(avtogenPath))
        {
            MessageBox.Show($"Файл {avtogenPath} не найден", "Ошибка", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        try
        {
            string[] lines = File.ReadAllLines(avtogenPath);
            Dictionary<string, string> statusDict = new Dictionary<string, string>();

            foreach (string line in lines)
            {
                if (line.Contains("Status_"))
                {
                    string[] parts = line.Split(':');
                    if (parts.Length == 2)
                    {
                        string key = parts[0].Trim();
                        string value = parts[1].Trim();
                        statusDict[key] = value;
                    }
                }
            }

            // Set background colors based on status
            foreach (DataGridViewRow row in dataGridView1.Rows)
            {
                if (row.Cells["Status"].Value != null)
                {
                    string status = row.Cells["Status"].Value.ToString();
                    string statusKey = "Status_" + status.Replace(" ", "_");

                    if (statusDict.ContainsKey(statusKey))
                    {
                        string statusValue = statusDict[statusKey].ToLower();
                        Color backgroundColor;

                        switch (statusValue)
                        {
                            case "готово":
                                backgroundColor = Color.LightGreen;
                                break;
                            case "не готово":
                                backgroundColor = Color.LightPink;
                                break;
                            case "в процессе":
                                backgroundColor = Color.LightBlue;
                                break;
                            default:
                                backgroundColor = Color.White;
                                break;
                        }

                        row.DefaultCellStyle.BackColor = backgroundColor;
                    }
                }
            }
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Ошибка при чтении файла: {ex.Message}", "Ошибка", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
} 