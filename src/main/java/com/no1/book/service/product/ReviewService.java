package com.no1.book.service.product;

import com.no1.book.domain.product.ReviewDto;
import org.springframework.stereotype.Service;

import java.util.List;


public interface ReviewService {

    void addReview(ReviewDto reviewDto);

    int getReviewCount();

    ReviewDto findReviewById(Integer reviewId);

    void deleleReviewById(Integer reviewId);

    void updateReview(ReviewDto reviewDto);

    List<ReviewDto> reviewsPerProduct(String prodId);

}
