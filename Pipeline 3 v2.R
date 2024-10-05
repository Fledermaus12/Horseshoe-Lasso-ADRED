# CONFIGURATION 
# hs or lx
modeltype <- 'lx'
id <- 'r03'
xscalelow = -2 # usually needs no change
xscalehigh = 2 # usually needs no change
trimmed = TRUE

p0 = 9  #say we are optimistic and expect 6-9 good predictors; there are x possible predictors here
p = 100


#######################



Sys.setenv(lang = "en_US")
library(ggplot2)
library(rstanarm)
library(magrittr)
library(dplyr)
library(bayesplot)
library(writexl)


filename <- paste0("programfiles/data-100_R_en_", id, ".csv")
data_o <- read.table(filename, header=T, sep=",")

print('Summary age')
summary(data_o$age)
print('Table sex')
table(data_o$sex)
print('Summary med amount')
summary(data_o$Med_Amount)
print('Summary med amount excluded')
summary(data_o$Med_Amount_Excluded)
print('Sum of Symptom')
print(sum(data_o$Symptom))
print('Sum of age')
print(sd(data_o$age))

data_o <- dplyr::mutate(data_o, age.z = scale(age))
data <- dplyr::select(data_o, -Med_Amount, -case_id, -patient, -age)

if (trimmed == TRUE ) {
  data <- data %>% select(-matches("Substrat|Inhibitor"))
} 

# rename columns
data <- data %>% rename("excluded drugs" = "Med_Amount_Excluded")
data <- data %>% rename("sex (female)" = "sex")
data <- data %>% rename("age (years)" = "age.z")

# print config.

print('configuration: ')
print(paste('id ', id))
print(paste('modeltype ', modeltype))
observation = nrow(data)
print(paste("p0 ", p0))
print(paste("p ", p))
print(paste("observation ", observation))


# run model


filename <- paste0("model_", id, "_", modeltype, ".rds")
# Check if the file exists
if (file.exists(filename)) {
  print("Model already exists. Load...")
  fit <- readRDS(filename)
  
} else {
  print("Model does not exist, run regression")
  
  global_scale = (p0/(p-p0))/sqrt(observation)  
  slab_scale = sqrt(0.3/p0)*sd(data$Symptom )   #0.3 somewhat arbitrary here
  
  if (modeltype == 'hs') {
    fit <- stan_glm(Symptom ~ . -Symptom, family = binomial, data = data, 
                    prior=hs(global_scale = global_scale, slab_scale = slab_scale))
  }
  if (modeltype == 'lx') {
    fit <- stan_glm(Symptom ~ . -Symptom, family = binomial, data = data,
                    prior=lasso())
  }
  filename <- paste0("model_", id, "_", modeltype, ".rds")
  saveRDS(fit, file = filename)
}

### prior 

plot <- plot(fit, pars = "beta") + scale_x_continuous(breaks = seq(xscalelow, xscalehigh, by = 0.1)) + theme(panel.grid = element_line(color = "gray", linetype = "dashed"))
plot <- plot + geom_vline(xintercept = 0)
print(plot)
filename <- paste0("model_", id, "_", modeltype, ".pdf")
ggsave(filename = filename, plot = plot, width = 15, height = 20, units = "in")




### print xlsx

posti <- posterior_interval(fit)
posti_df <- as.data.frame(posti)
posti_df$Parameter <- rownames(posti_df)

#Median
posterior_samples <- as.matrix(fit)
medians <- apply(posterior_samples, 2, median)
posti_df$Median <- medians
set1 <- posti_df

posti <- posterior_interval(fit, prob=0.5)
posti_df <- as.data.frame(posti)
posti_df$Parameter <- rownames(posti_df)
set2 <- posti_df


# Merge the data frames based on the "Parameter" column
df <- merge(set1, set2, by = "Parameter")

# Select specific columns
df <- df %>% select(Parameter, `5%`, `25%`, Median, `75%`, `95%`)

# Write the result to an Excel file
# Define file names
filename <- paste0("model_", id, "_", modeltype, ".xlsx")
write_xlsx(df, filename)

