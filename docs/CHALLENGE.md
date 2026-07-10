# The certification

This challenge aims to assess your analytical reasoning, visualization creation, and data-driven argumentation skills. By applying the techniques and tools presented throughout the course, earning this certification indicates that you:

* Understands the process of building a modern analytics platform;
* Understands the objectives of dimensional modeling in modern data warehouses;
* Knows how to apply SQL and use transformation tools to model data in modern data warehouses;
* Is familiar with data visualization best practices and their application in a BI tool.

## 1. General Context

You have been hired by Adventure Works (AW), a rapidly growing bicycle manufacturer that boasts over 500 distinct products, 20,000 customers, and 31,000 orders. To sustain its growth and differentiate itself from the competition, Adventure Works aims to use its data strategically, guiding its decisions to become a data-driven company. The company's leadership has already listed a series of questions they wish to answer through data analysis—questions that will guide the development of the data warehouse's fact and dimension tables. To kickstart the project and achieve quick results, the decision was made to begin with the sales area, although tables from other areas may be required to obtain the desired information. In your initial assessment, you identified several systems used by Adventure Works that generate business-relevant data and should eventually be integrated into the data infrastructure:

| Function | System |
|---|---|
| ERP | SAP |
| CRM | Salesforce |
| Web Analytics | Google Analytics |
| Website | Wordpress |

During initial conversations, you also identified that the project does not have unanimous support within the company; there are doubts regarding the timeline, the costs involved, and whether there will be a return on investment.

The project was conceived and sponsored by AW's Innovation Director, João Muller, and also has the backing of the company's CEO, Carlos Silveira, who views the use of data as a long-term strategic differentiator. However, the Commercial Director, Silvana Teixeira, believes the funds invested in the project could have been allocated to promotional activities that—in her view—generate immediate sales results. Furthermore, she fails to see how creating a modern data infrastructure will benefit her commercial department, given that previous promises to make the area "data-driven"—made by vendors of other systems like CRM and Web Analytics—failed to deliver the promised results.

A specific request from CEO Carlos Silveira is that the construction of this data platform guarantees the quality and accuracy of the output data; in other words, the Analytics Engineering team must be able to confirm that the information aligns with the figures verified by the accounting audit team. Carlos cited the example of gross sales in 2011, which totaled $12,646,112.16. He would like tests performed to verify the accuracy of this figure within the models being built, following the approach from a "Modern Data Stack" workshop he recently attended.

In addition to these individuals, the IT Director, Nilson Ramos, is responsible for ensuring data access and has designated an analyst, Gabriel Santos, to assist with this. Gabriel is currently responsible for managing databases and answering ad-hoc questions from business units that require SQL. His schedule is quite tight, so coordinated communication and efficient interactions are essential to ensure all necessary data is available for the project.

### Data description

Adventure Works has a transactional database (PostgreSQL) that stores data from its various areas. This data is distributed across 68 tables divided into 5 schemas: HR (Human Resources), sales (vendas), production (produção), and purchasing (compras).

To take a look at the complete diagram, see [here](AdventureWorksERD.jpeg).

## 2. Challenge objective

The goal is to build a data model for conducting clear and reliable analyses using a base dataset derived from Adventure Works raw data, enabling you to answer the following business questions:

a. What are the number of orders, quantity purchased, and total transaction value by product, card type, sales reason, sales date, customer, status, city, state, and country?

b. Which products have the highest average order value by month, year, city, state, and country? (average order value = Gross revenue - product discounts / number of orders in the analysis period)

c. Who are the top 10 customers by total transaction value, filtered by product, card type, sales reason, sales date, status, city, state, and country?

d. Which are the top 5 cities by total transaction value, filtered by product, card type, sales reason, sales date, customer, status, city, state, and country?

e. What are the number of orders, quantity purchased, and total transaction value by month and year (hint: time series chart)?

f. Which product has the highest number of units purchased for the "Promotion" sales reason?

## 3. Preparation for the challenge

**Data ingestion instructions (EL):**

Before starting the challenge, you will need to ingest the Adventure Works data. Follow the prerequisite instructions and the initial setup tutorial on the repository's main page. At the bottom of the main instructions page, you will find links directing you to the specific instructions for each track.

**USE ONLY THE `adventure_works` SCHEMA FOR THE CHALLENGE.**

## 4. Challenge steps

To develop the deliverables, it is essential to complete the following steps:

1. Research and definition of KPIs and business questions relevant to Adventure Works' business context. You must propose which indicators should be tracked on the dashboard and provide a justification;
2. Creation of an exploratory data analysis to gain insights and a presentation explaining how these insights contributed to understanding the dataset;
3. Conceptual data warehouse diagram in PDF format: create a conceptual model featuring the fact and dimension tables necessary to answer the business questions listed in the objective. Briefly indicate the source tables used to create each dimension table and the fact table. (Suggested tool: draw.io)
4. Cloud data warehouse setup and dbt configuration. Suggestion: Databricks Free Edition and dbt Cloud.
5. Data transformation: transform raw data using dbt (suggestion: dbt Cloud). This transformation must include the following elements:
   1. documentation of tables and columns in data marts
   2. source tests
   3. tests on primary keys for dimension and fact tables
   4. data quality tests
   5. The code must be hosted in a repository (suggestion: GitHub). You must provide the link to the GitHub repository.
6. Creation of a dashboard mockup, based on your KPI research and insights from the exploratory data analysis. Pay attention to data visualization and data storytelling best practices;
7. Dashboard development, following the logic established in the mockup and utilizing inputs derived from the KPI definitions and exploratory data analysis, while also answering the minimum questions listed in the challenge objective. These are the minimum questions that must be answered via analyses performed on the created dashboard; however, a complete and well-structured dashboard will also factor into the final evaluation of the BI component;
8. Documentation of business rules;
9. Creation of a final presentation and video recording. Video: you must record a video presenting all project stages (DW, EL, dbt transformation, and BI). Create it using a recording tool, such as Nimbus or OBS Studio. The video should not exceed 10 minutes in length. You can use YouTube or another platform if you wish.

Below is a basic narrative structure to guide your video. You can include additional information—such as modeling decisions, custom metrics, and various insights derived from your dashboard—but it is essential that your video includes the following demonstrations:

* A brief explanation of the project's objective and expected results.
* An explanation of the created dimension tables and their relationship with the fact table.
* A demonstration of `dbt run` showing that all models execute successfully.
* A demonstration showing that all tests applied to the source pass. Use `dbt test –select source:*`.
* A demonstration showing that all tests applied to the models pass. Use `dbt test`.
* A demonstration of the fact table and the joins performed between the fact table and the dimension tables; an explanation of which metrics were created in the fact table and why.
* Presentation of the data testing.
* Presentation of the dashboard, including how filters work, the visualizations, and the analysis possibilities.

**[OPTIONAL]**

Data project planning (PDF format): consider the information gathered during the initial assessments, which is summarized in the context section. Pay particular attention to the project's expected objectives, stakeholders, and risks/contingencies. Additionally, what other value can be derived from data infrastructure projects? Are there other risks and contingencies you consider relevant to include in the project plan? (Please use the template provided in the attachment at the top right of the page.)

## 5. Presentation and submission of the challenge

You must deliver:

1. Notebook containing exploratory and explanatory data analysis in Python or SQL. The notebook must include code, charts, and commentary on each insight from the EDA phase;
2. PDF file of the conceptual model;
3. Link to the dbt repository containing the transformed models;
4. JPEG file of the dashboard mockup created in Figma;
5. A Power BI or Databricks AI/BI dashboard focused on the commercial area. For Power BI, submit the PBIX file with all DAX measures documented within the file. If using Databricks AI/BI, provide the dashboard link and the JSON file;
6. File containing documentation of business rules;
7. Presentation (slides) covering the project stages, including arguments regarding data-driven culture, insights derived from the EDA, justification for the choice of indicators and dashboard visuals, a walkthrough of the dashboard and its key features, and finally, recommendations for actionable initiatives for the client based on the established objective;
8. A 3-to-5-minute video presenting the project. It is essential to include a demonstration of the dashboard in action and show the modeling used within the BI tool (whether Power BI or Databricks AI/BI).

All project steps must be archived in a WinRAR file or Zip folder and submitted via the platform as follows:

1. GitHub: você deve entregar todo o projeto de transformação no GitHub através de um link em um arquivo de texto na pasta.
2. BI: Se o BI desenvolvido for no AI/BI, disponibilizar o link em um arquivo de texto na pasta
3. Youtube/Drive/Dropbox: você deve inserir o vídeo em alguma dessas plataformas através de um link em um arquivo de texto na pasta.
4. Modelo Conceitual: você deve exportar e inserir o Modelo Conceitual do Projeto Final na pasta de WinRAR ou Zip.
5. Apresentação, Mockup e outros arquivos: você deve exportar em JPEG/PDF e inserir na pasta de WinRAR ou ZIP, não esqueça de adicionar o arquivo de texto com os links.

**Nota:** If this folder exceeds Moodle's 40 MB limit, you can compress the entire project into a WinRAR or Zip file, upload it to a Google Drive folder, and send us the link via a text file. Please remember that access to any links provided must be set to public to expedite the grading process.

## 6. What will be evaluated

Our assessment is based on a total of 10 points and considers criteria such as:

* Adherence to delivery requirements;
* Professionalism in delivery and presentation;
* Clarity/understanding of the content;

The minimum passing score is 7. You have 30 days after registering to submit the challenge. If you do not meet the requirement, you will have a second chance to correct any areas that were insufficient.

The criteria for student approval will be as follows:

1. Understanding of the business and a focus on addressing client needs;
2. Analytical ability to define metrics and visualizations that are meaningful and provide actionable insights for the client;
3. Exploratory Data Analysis (EDA) and well-structured, organized conceptual diagrams, accompanied by documentation of insights;
4. Understanding of and organizational skills for data transformation and data modeling projects, along with basic knowledge of Git;
5. Dashboard creation that answers key business questions while adhering to best practices in data visualization, user experience (UX), and data storytelling, including documentation and data validation;
6. Ability to generate actionable recommendations based on analyses and articulate the importance of a data-driven culture—bearing in mind that the Commercial Director is unaware of the potential of data to improve performance;
7. Presentation of the solution covering all stages of the challenge.
