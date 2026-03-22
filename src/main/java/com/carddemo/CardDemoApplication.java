package com.carddemo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * CardDemo Online Application
 * Modernized from AWS CardDemo CICS COBOL application
 * Original: https://github.com/aws-samples/aws-mainframe-modernization-carddemo
 */
@SpringBootApplication
public class CardDemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(CardDemoApplication.class, args);
    }
}
