import streamlit as st
import pandas as pd



def read_sales_data(file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name)
    id_cols = ['ASIN', 'Product Name']
    date_cols = [col for col in df.columns if col not in id_cols]
    melted_df = df.melt(id_vars=id_cols, value_vars=date_cols,
                        var_name='Date', value_name='Sales')
    melted_df['Date'] = pd.to_datetime(melted_df['Date'], format='%Y%m%d')
    return melted_df

def read_gross_profit(gross_profit_file, sheet_name):
    df = pd.read_excel(gross_profit_file, sheet_name)
    id_cols = ['ASIN', 'Product Name']
    date_cols = [col for col in df.columns if col not in id_cols]
    melted_df = df.melt(id_vars=id_cols, value_vars=date_cols,
                        var_name='Date', value_name='Gross Profit')
    melted_df['Date'] = pd.to_datetime(melted_df['Date'], format='%Y%m%d')
    return melted_df

def inventory_preprocessing(inventory_file, sheet_name):
    df = pd.read_excel(inventory_file, sheet_name)
    df = df.drop(['sku', 'product-name'], axis=1)
    df['Total_inventory'] = df['available'] + df['Reserved FC Transfer'] + df['Reserved FC Processing']
    df['ASIN'] = df['asin']
    inventory_df = df.drop(['snapshot-date', 'available', 'Reserved FC Transfer', 'Reserved FC Processing', 'asin'], axis=1)
    return inventory_df

def calculate_drr_7(Combined_data_file):

    if isinstance(Combined_data_file, str):
        Combined_data_file = pd.read_csv(Combined_data_file)


    Combined_data_file = Combined_data_file.sort_values(['ASIN', 'Date']


    )

    Combined_data_file['Daily_Retail_Rate'] = (
        Combined_data_file.groupby('ASIN')['Sales']
        .rolling(window=5, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
    )

    Combined_data_file['Daily_Retail_Rate'] = Combined_data_file['Daily_Retail_Rate'].round()


    # Combined_data_file.to_csv("Drr@7.csv", index=False)

    return Combined_data_file

def calculate_moving_averages(merged_data):
    merged_data = merged_data.sort_values('Date')
    merged_data['Sales_moving_averages'] = merged_data['Sales'].rolling(window=7, center=True).mean().round()
    merged_data['Gross_profit_moving_averages'] = merged_data['Gross Profit'].rolling(window=7, center=True).mean().round()
    return merged_data

def calculate_inventory_status(drr_df, inventory_df):
    inventory_status = pd.merge(inventory_df, drr_df, on='ASIN', how='left')
    inventory_status['Days_of_Inventory'] = inventory_status['Total_inventory'] / inventory_status['Daily_Retail_Rate'].round()

    def get_restocking_recommendation(days):
        if pd.isna(days):
            return 'No Sales Data'
        elif days <= 20:
            return 'Urgent Restock'
        elif days <= 80:
            return 'Restock Soon'
        elif days <= 100:
            return 'Monitor Inventory'
        else:
            return 'Sufficient Inventory'
    
    inventory_status['Restocking_Recommendation'] = inventory_status['Days_of_Inventory'].apply(get_restocking_recommendation)
    return inventory_status

def Complete_report(file1,file2,file3):
  df = pd.merge(pd.merge(file1,file2, on = ['ASIN', 'Date'], how = 'inner'),file3 , on = ['ASIN', 'Date'], how = 'inner')
  df = df.drop(['Product Name_x_y','Product Name_y_x','Product Name_y_y','Sales_y','Gross Profit_y','Product Name_x','Sales','Product Name_y','Gross Profit'],axis= 1)
#   df.to_csv('final report.csv')
  return df




def main():
    st.title('Sales and Inventory Analysis Dashboard')

    # Sidebar for file uploads
    st.sidebar.header('Upload Files')
    data_file = st.sidebar.file_uploader('Upload Sales Data Excel File', type=['xlsx'])
    # gross_profit_file = st.sidebar.file_uploader('Upload Gross Profit Excel File', type=['xlsx'])
    # inventory_file = st.sidebar.file_uploader('Upload Inventory Excel File', type=['xlsx'])

    # Sheet name input
    sales_sheet = st.sidebar.text_input('Sales Sheet Name', 'Sales')
    gross_profit_sheet = st.sidebar.text_input('Gross Profit Sheet Name', 'Profit')
    inventory_sheet = st.sidebar.text_input('Inventory Sheet Name', 'Inventory')

    if data_file and data_file and data_file:
        try:
            # Process files
            sales_data = read_sales_data(data_file, sales_sheet)
            gross_profit_data = read_gross_profit(data_file, gross_profit_sheet)
            
            # Combine sales and gross profit data
            combined_data = pd.merge(sales_data, gross_profit_data, on=['ASIN', 'Date'], how='inner')
            
            # Calculate Daily Retail Rate
            drr_data = calculate_drr_7(combined_data)
            
            # Calculate Moving Averages
            moving_avg_data = calculate_moving_averages(drr_data)
            
            # Process Inventory
            inventory_data = inventory_preprocessing(data_file, inventory_sheet)
            
            # Calculate Inventory Status
            inventory_status = calculate_inventory_status(drr_data, inventory_data)

            final_df = Complete_report(moving_avg_data,combined_data,drr_data)

            # Tabs for different views
            tab1, tab2= st.tabs(['Sales data','Inventory Status'])


            with tab1:
                st.header('Sales Data')
                
                selected_asin = st.selectbox(
                    'Select ASIN for Detailed View',
                    ['All'] + list(drr_data['ASIN'].unique()),
                    key='sales_asin_select'
                )
    
                if selected_asin != 'All':
                    asin_data = drr_data[drr_data['ASIN'] == selected_asin]
                else:
                    asin_data = drr_data  # If 'All' is selected, use the entire dataset
    
                selected_date = st.selectbox(
                    'Select Date for Detailed View',
                    ['All'] + list(asin_data['Date'].unique()),
                    key='sales_date_select'
                )
    
                if selected_date != 'All':
                    product_data = asin_data[asin_data['Date'] == selected_date]
                else:
                    product_data = asin_data  # Only filter by ASIN or show all data

                st.dataframe(product_data[['Date', 'ASIN', 'Product Name_x', 'Sales', 'Gross Profit']])

            with tab2:
                st.header('Inventory Status')
   
                selected_asin = st.selectbox(
                    'Select ASIN for Detailed View',
                    ['All'] + list(inventory_status['ASIN'].unique()),
                    key='inventory_asin_select'
                )
    
                if selected_asin != 'All':
                    asin_data = inventory_status[inventory_status['ASIN'] == selected_asin]
                else:
                    asin_data = inventory_status  # If 'All' is selected, use the entire dataset
    
                selected_date = st.selectbox(
                    'Select Date for Detailed View',
                    ['All'] + list(asin_data['Date'].unique()),
                    key='inventory_date_select'
                )
    
                if selected_date != 'All':
                    product_data = asin_data[asin_data['Date'] == selected_date]
                else:
                    product_data = asin_data  # Only filter by ASIN or show all data
 
                st.dataframe(product_data[['Date', 'Total_inventory', 'ASIN', 'Product Name_x', 'Sales', 'Daily_Retail_Rate', 'Days_of_Inventory', 'Restocking_Recommendation']])
    


        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning('Please upload all required files.')

if __name__ == '__main__':
    main()
